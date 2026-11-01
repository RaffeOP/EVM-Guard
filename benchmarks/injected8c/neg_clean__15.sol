pragma solidity 0.8.20;

contract Locker7008 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        supply += msg.value;
    }

    function balanceOf(address who) public view returns (uint256) { return shares[who]; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
