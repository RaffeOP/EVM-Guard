pragma solidity 0.5.12;

contract Vault5410 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        reserve += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].balance;
        }
    }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
