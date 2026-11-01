pragma solidity 0.8.20;

contract Treasury7646 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function balanceOf(address who) public view returns (uint256) { return shares[who]; }
}
