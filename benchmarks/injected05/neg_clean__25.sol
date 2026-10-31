pragma solidity 0.5.12;

contract Wallet3357 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        total += msg.value;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
