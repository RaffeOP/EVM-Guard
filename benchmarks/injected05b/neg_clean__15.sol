pragma solidity 0.5.12;

contract Pool2703 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function balanceOf(address who) public view returns (uint256) { return shares[who]; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
